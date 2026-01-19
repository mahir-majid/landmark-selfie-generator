# Token Association for Targeted Identity Injection in InfiniteYouService

## Problem Statement

### Current Issue
The InfiniteYouService currently applies face identity embeddings **globally** to the entire image, leading to inconsistent results when prompts contain multiple people. For example, with the prompt "a man and woman at the beach":

- **Sometimes**: Identity affects the man (gender bias from male input image)
- **Sometimes**: Identity affects the woman (attention focuses there)
- **Sometimes**: Identity affects both people (attention spreads)
- **Sometimes**: Identity affects neither (attention misses)

### Root Cause
The current architecture has **no mechanism for token-specific identity injection**:

```python
# Current flow in pipeline_flux_infusenet.py (Lines 550-580)
controlnet_block_samples, controlnet_single_block_samples = self.controlnet(
    encoder_hidden_states=controlnet_prompt_embeds,  # ← Global face identity
    txt_ids=controlnet_text_ids,                     # ← Global token structure
    # ...
)

noise_pred = self.transformer(
    encoder_hidden_states=prompt_embeds,            # ← Natural text embeddings
    txt_ids=text_ids,                               # ← Natural token structure
    controlnet_block_samples=controlnet_block_samples,  # ← Global identity injection
    # ...
)
```

**Face identity is applied to the ENTIRE image**, not specific text tokens like "PERSON_1".

### Desired Solution
Implement **token-specific identity injection** that allows users to specify which tokens (e.g., "PERSON_1", "boy", "girl") should receive the face identity from the input image, while preserving natural text understanding.

## Solution Strategy

### Focus Areas
Based on architectural analysis, we should focus on **InfuseNet components** while preserving natural text processing:

#### **Primary Targets (Modify These)**
1. **`controlnet_prompt_embeds`** - Face identity features for InfuseNet
2. **`controlnet_text_ids`** - Token structure for InfuseNet attention
3. **`controlnet_block_samples`** - Identity-influenced features passed to main transformer

#### **Preserve These (Leave Alone)**
1. **`prompt_embeds`** - Natural text understanding for main transformer
2. **`pooled_prompt_embeds`** - Global text context for guidance mechanisms

### Implementation Approach

#### **Super Simple Solution: Target Token Only**
```python
# First encode_prompt call (lines 323-339) - Keep Original
(
    prompt_embeds,
    pooled_prompt_embeds,
    text_ids,
) = self.encode_prompt(
    prompt=prompt,  # ← "PERSON_1 and woman at the beach" (unchanged)
    prompt_2=prompt_2,
    prompt_embeds=prompt_embeds,
    pooled_prompt_embeds=pooled_prompt_embeds,
    device=device,
    num_images_per_prompt=num_images_per_prompt,
    max_sequence_length=max_sequence_length,
    lora_scale=lora_scale,
)

# Second encode_prompt call (lines 356-371) - Just Target Token
if infu_source_img_token and infu_source_img_token in prompt:
    infusenet_prompt = infu_source_img_token  # ← Just the target token!
else:
    infusenet_prompt = prompt

(
    controlnet_prompt_embeds,
    pooled_prompt_embeds,
    controlnet_text_ids,
) = self.encode_prompt(
    prompt=infusenet_prompt,  # ← "PERSON_1" only
    prompt_2=prompt_2,
    prompt_embeds=controlnet_prompt_embeds,
    pooled_prompt_embeds=pooled_prompt_embeds,
    device=device,
    num_images_per_prompt=num_images_per_prompt,
    max_sequence_length=max_sequence_length,
    lora_scale=lora_scale,
)
```

#### **How This Works**
1. **First `encode_prompt`**: Full prompt for main transformer (natural text understanding)
2. **Second `encode_prompt`**: Just target token for InfuseNet (token-specific identity)
3. **InfuseNet**: Only processes the target token, so identity only applies there
4. **Main transformer**: Gets full context but identity injection is already token-specific

## Technical Implementation

### **Location**: `pipeline_flux_infusenet.py`
**Insertion Point**: After line 339 (after first `encode_prompt` call), before the second one (line 356)

### **Key Function Needed**:
```python
def get_infusenet_prompt(original_prompt, target_token):
    """Get target token for InfuseNet processing"""
    if target_token and target_token in original_prompt:
        return target_token  # Just the target token
    else:
        return original_prompt  # Fallback to original
```

### **Integration Point**:
```python
# After first encode_prompt (line 339)
if infu_source_img_token:
    infusenet_prompt = get_infusenet_prompt(prompt, infu_source_img_token)
else:
    infusenet_prompt = prompt

# Second encode_prompt (line 356-371) - Use infusenet_prompt
```

## Benefits of This Approach

### **Ultra Simplicity**
- ✅ **Minimal code changes** - Just change the prompt string
- ✅ **No complex processing** - Let the model handle everything
- ✅ **Easy to understand** - Crystal clear implementation
- ✅ **Easy to debug** - Simple to trace what's happening

### **Preserves Natural Text Understanding**
- ✅ **`prompt_embeds`** gets full context for proper text comprehension
- ✅ **`pooled_prompt_embeds`** maintains global context
- ✅ **Main transformer** processes complete prompt naturally

### **Targets Identity Injection Specifically**
- ✅ **`controlnet_text_ids`** only contains target token structure
- ✅ **`controlnet_prompt_embeds`** only processes target token
- ✅ **`controlnet_block_samples`** naturally processes token-specific identity

### **Maintains Architecture Integrity**
- ✅ **Works with existing pipeline** without major changes
- ✅ **Preserves all existing functionality**
- ✅ **Clean separation of concerns**

## Expected Results

### **Before Implementation**
```
Prompt: "a man and woman at the beach"
Result: Random identity assignment (man, woman, both, or neither)
```

### **After Implementation**
```
Main Transformer Prompt: "PERSON_1 and woman at the beach"
InfuseNet Prompt: "PERSON_1"
Result: Consistent identity injection to "PERSON_1" token only
```

## Limitations & Considerations

### **Current Limitations**
- **Single token support** - Initially supports one target token per prompt
- **Token dependency** - Requires exact token matching
- **Simple approach** - May need refinement based on testing

### **Future Enhancements**
- **Multiple tokens** - Support for multiple identity tokens in one prompt
- **Fuzzy matching** - Support for partial token matches
- **Dynamic tokenization** - Handle different tokenizer strategies

## Conclusion

This **ultra-simple approach** provides the **best balance** of:
- **Technical feasibility** - Uses existing architecture
- **Implementation simplicity** - Just change the prompt string
- **Effectiveness** - Directly targets identity injection mechanism
- **Maintainability** - Crystal clear and easy to understand

By simply passing the target token to the second `encode_prompt` call, we can achieve token-specific identity injection while preserving natural text understanding in the main transformer. This approach is so clean and simple that it's definitely worth trying! 