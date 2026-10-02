# RIO Product Creative Agent SOP

## Product Input & Asset Source Policy

### Source Priority Order:
1. **HERMES_PROVIDED** - Verified product package from Hermes (canonical source)
2. **USER_PROVIDED** - Direct images, URLs, specifications from user
3. **SOURCE_REQUIRED** - Product ID/ASIN/URL from approved sources only

### Safety Rules:
- NEVER assume or invent product identity
- NEVER substitute visually similar products
- SAFE_STOP if exact product cannot be verified

### Pre-Creation Checklist:
- [ ] Product identity verified
- [ ] Source URL or product ID available
- [ ] Primary product image available
- [ ] Product data (price, description) available
- [ ] Affiliate destination known (for CTA)
- [ ] Image provenance maintained

### Image Provenance Required:
- `image_source`
- `source_url`
- `product_id`
- `retrieved_at`
- `asset_type`
- `verification_status`

### What Agent Can Generate:
- Backgrounds
- Lifestyle scenes
- Graphics & icons
- Typography
- Shadows
- Promotional composition

### What Agent Cannot Do:
- Replace verified product with AI-invented alternative
- Assume product details without verification

## Output Quality Standards:
- 1080x1350 pixels minimum
- High readability text
- Amazon Associate branding
- Clear CTA buttons
- Professional layout

## Files:
- `products/` - Source product data
- `assets/` - Product images
- `output/` - Generated flyers
- `provenance/` - Image tracking JSON
