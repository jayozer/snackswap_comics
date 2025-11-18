# SnackSwap Comics - Implementation TODO

## 🎯 Project Goal
Implement comic rendering using Nano-Banana (Gemini 2.5 Flash Image) and Freepik API, plus a frontend to display the generated comics.

---

## 📋 Phase 1: Backend - Comic Rendering Service

### 1.1 Nano-Banana Service ⏳
- [ ] Create `app/services/nanobana_service.py`
- [ ] Implement `NanoBananaService` class
  - [ ] `generate_comic_image()` method - takes script, returns 4-panel image
  - [ ] Build detailed visual prompts from script panels
  - [ ] Handle Gemini 2.5 Flash Image API calls
  - [ ] Implement character consistency techniques
  - [ ] Error handling and retry logic
  - [ ] Rate limit handling
- [ ] Add configuration for Nano-Banana model
- [ ] Add unit tests

### 1.2 Freepik Integration Service ⏳
- [ ] Create `app/services/freepik_service.py`
- [ ] Implement `FreepikService` class
  - [ ] `search_assets()` - search for comic elements
  - [ ] `download_asset()` - fetch and cache assets
  - [ ] Asset caching system (avoid re-downloading)
  - [ ] Search for speech bubbles, frames, backgrounds
  - [ ] Handle API authentication
  - [ ] License tracking for assets
- [ ] Add Freepik API key to configuration
- [ ] Add unit tests

### 1.3 Comic Rendering Service ⏳
- [ ] Create `app/services/render_service.py`
- [ ] Implement `RenderService` class
  - [ ] `render_comic()` - main orchestration method
  - [ ] **Step 1**: Parse script and extract panel data
  - [ ] **Step 2**: Generate 4-panel image with Nano-Banana
  - [ ] **Step 3**: (Optional) Fetch Freepik assets
  - [ ] **Step 4**: Composite image with Pillow
  - [ ] **Step 5**: Add text overlays (dialogue, captions)
  - [ ] **Step 6**: Generate 3 export formats:
    - [ ] Square: 1080x1080 (Instagram, TikTok)
    - [ ] Portrait: 1080x1350 (Stories, Pinterest)
    - [ ] Reel: Custom dimensions
  - [ ] Save to storage with proper naming
  - [ ] Generate alt text and metadata
- [ ] Add helper functions for text rendering
- [ ] Add helper functions for image composition
- [ ] Add unit tests

### 1.4 Update Render API Endpoint ⏳
- [ ] Update `app/api/render.py`
- [ ] Replace placeholder implementation with real rendering
- [ ] Integrate `RenderService`
- [ ] Update response to return real URIs
- [ ] Add proper error handling
- [ ] Add logging for monitoring
- [ ] Test endpoint with curl

### 1.5 Configuration & Environment ⏳
- [ ] Add `NANOBANA_MODEL` to `.env` (default: `gemini-2.5-flash-image`)
- [ ] Verify `FREEPIK_API_KEY` is set
- [ ] Add rendering config options:
  - [ ] `COMIC_OUTPUT_QUALITY` (JPEG quality)
  - [ ] `COMIC_SQUARE_SIZE` (default: 1080)
  - [ ] `COMIC_PORTRAIT_SIZE` (default: 1080x1350)
  - [ ] `ENABLE_FREEPIK_ASSETS` (toggle Freepik integration)
- [ ] Update `.env.example` with new variables
- [ ] Document all new config options in README

---

## 📋 Phase 2: Frontend Development

### 2.1 Setup Frontend Structure ⏳
- [ ] Create `frontend/` directory
- [ ] Choose approach: Simple HTML/JS or React
- [ ] Set up basic file structure
- [ ] Add styling framework (Tailwind CSS or plain CSS)

### 2.2 Build Comic Viewer Interface ⏳
- [ ] Create main HTML page (`index.html`)
- [ ] **Upload Section**:
  - [ ] File upload button
  - [ ] Image preview
  - [ ] Age input field
  - [ ] Allergies input (optional)
- [ ] **Processing Indicators**:
  - [ ] Loading spinner during API calls
  - [ ] Step-by-step progress (Detection → Scoring → Script → Rendering)
- [ ] **Results Display**:
  - [ ] Show detected food items with confidence
  - [ ] Display dental risk score with visual indicator (color-coded)
  - [ ] Show educational facts used in comic
  - [ ] Display final 4-panel comic strip
- [ ] **Download Options**:
  - [ ] Download square format button
  - [ ] Download portrait format button
  - [ ] Download reel cover button
  - [ ] Share to social media (optional)

### 2.3 API Integration ⏳
- [ ] Create `app.js` for frontend logic
- [ ] Implement API client functions:
  - [ ] `uploadImage()` - POST /api/capture/intake
  - [ ] `detectItems()` - POST /api/vision/detect
  - [ ] `scoreAndRetrieve()` - POST /api/score/retrieve
  - [ ] `composeScript()` - POST /api/script/compose
  - [ ] `renderComic()` - POST /api/render/comic
- [ ] Handle API responses and errors
- [ ] Update UI based on API responses
- [ ] Add retry logic for failed requests

### 2.4 Responsive Design ⏳
- [ ] Mobile-friendly layout
- [ ] Tablet optimization
- [ ] Desktop optimization
- [ ] Touch-friendly buttons
- [ ] Accessible alt text and labels

### 2.5 CORS & Serving ⏳
- [ ] Ensure FastAPI CORS is configured for frontend
- [ ] Serve frontend via FastAPI static files OR separate server
- [ ] Test cross-origin requests

---

## 📋 Phase 3: Testing & Documentation

### 3.1 Backend Testing ⏳
- [ ] Test Nano-Banana image generation with sample scripts
- [ ] Test Freepik asset fetching
- [ ] Test complete rendering pipeline
- [ ] Test all 3 export formats
- [ ] Test with different snack types
- [ ] Performance testing (rendering time)
- [ ] Error scenario testing

### 3.2 Frontend Testing ⏳
- [ ] Test upload flow
- [ ] Test API integration
- [ ] Test display of results
- [ ] Test download functionality
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Mobile device testing

### 3.3 End-to-End Testing ⏳
- [ ] Upload gummy bears image
- [ ] Verify detection works
- [ ] Verify scoring and facts retrieval
- [ ] Verify script composition
- [ ] **Verify comic rendering produces visual comic**
- [ ] Download and inspect all 3 formats
- [ ] Test with different age groups

### 3.4 Documentation ⏳
- [ ] Update README.md with rendering setup
- [ ] Document Nano-Banana API setup
- [ ] Document Freepik API setup
- [ ] Add frontend usage instructions
- [ ] Add troubleshooting guide
- [ ] Add example screenshots/comics

---

## 📋 Phase 4: Polish & Deployment

### 4.1 Code Quality ⏳
- [ ] Code review
- [ ] Refactor any duplicated code
- [ ] Add type hints where missing
- [ ] Run linter (ruff/black)
- [ ] Optimize performance bottlenecks

### 4.2 Error Handling ⏳
- [ ] User-friendly error messages
- [ ] Graceful degradation if Freepik fails
- [ ] Fallback if Nano-Banana quota exceeded
- [ ] Logging for debugging

### 4.3 Production Readiness ⏳
- [ ] Environment variable validation
- [ ] API key security audit
- [ ] Rate limiting protection
- [ ] Database persistence for rendered comics (optional)
- [ ] CDN setup for comic storage (optional)

---

## 🎯 Current Status

**Completed:**
- ✅ FastAPI backend setup
- ✅ Qdrant vector database
- ✅ Gemini vision detection
- ✅ Script composition
- ✅ Pillow installed
- ✅ Research on Nano-Banana and Freepik

**In Progress:**
- ⏳ Backend rendering implementation
- ⏳ Frontend development

**Next Up:**
1. Create NanoBananaService
2. Create FreepikService
3. Create RenderService
4. Update render endpoint
5. Build simple frontend viewer

---

## 📝 Notes

### Nano-Banana (Gemini 2.5 Flash Image)
- API: `gemini-2.5-flash-image` model
- Cost: ~$0.039 per comic
- Rate limit (free): 500 images/day
- Documentation: https://ai.google.dev/gemini-api/docs/image-generation

### Freepik API
- Free API key available
- Pay-as-you-go pricing
- Search for: comic speech bubbles, panel borders, backgrounds
- Documentation: https://docs.freepik.com/

### Comic Rendering Strategy
- Generate entire 4-panel comic in one Nano-Banana call
- Use detailed prompt with all panel descriptions
- Optionally overlay Freepik assets for polish
- Use Pillow for text and final composition

---

## ✅ Definition of Done

**Backend:**
- [ ] `/api/render/comic` returns actual comic images
- [ ] Comics are visually appealing with clear characters
- [ ] Educational facts are visible and readable
- [ ] All 3 formats export correctly

**Frontend:**
- [ ] Users can upload images
- [ ] Comic displays in browser
- [ ] Download buttons work
- [ ] Mobile-friendly

**Overall:**
- [ ] End-to-end test passes with gummy bears image
- [ ] Documentation is complete
- [ ] Code is production-ready


**Issues to fix:**
- [ ]The bubbles do not have correct text. need to add text with comic sans and replace it. It has to be an overlay