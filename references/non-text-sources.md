# Non-Text Lock-In — Authoritative References

## Tier 1: Standards & Official Documentation

### REF-F1: W3C WCAG 2.2 — SC 1.1.1: Non-text Content
- **Organization**: W3C
- **URL**: https://www.w3.org/WAI/WCAG22/Understanding/non-text-content.html
- **Mechanism Supported**: lock-in (F-001, F-003)
- **Claim Supported**: All non-text content presented to the user must have a text alternative that serves an equivalent purpose. Decorative images should use `alt=""`.
- **What It Does NOT Establish**: Impact on AI extraction specifically.
- **Evidence Type**: SOURCE-DERIVED FACT

### REF-F2: W3C WCAG 2.2 — SC 1.2.1, 1.2.2: Time-based Media
- **Organization**: W3C
- **URL**: https://www.w3.org/WAI/WCAG22/Understanding/captions-prerecorded.html
- **Mechanism Supported**: lock-in (F-003)
- **Claim Supported**: Pre-recorded audio/video content requires captions (1.2.2) and descriptions (1.2.1). Text alternatives must convey the same information.
- **What It Does NOT Establish**: AI-specific behavior with video content.
- **Evidence Type**: SOURCE-DERIVED FACT

### REF-F3: WHATWG HTML Specification — Canvas Element
- **Organization**: WHATWG
- **URL**: https://html.spec.whatwg.org/multipage/canvas.html
- **Mechanism Supported**: lock-in (F-003)
- **Claim Supported**: "Authors should provide alternative content inside the canvas element" for non-visual consumption. Canvas pixel data is not accessible to text extraction.
- **What It Does NOT Establish**: Whether AI systems can interpret canvas content.
- **Evidence Type**: SOURCE-DERIVED FACT

### REF-F4: WHATWG HTML Specification — Video Element
- **Organization**: WHATWG
- **URL**: https://html.spec.whatwg.org/multipage/media.html#the-video-element
- **Mechanism Supported**: lock-in (F-003)
- **Claim Supported**: `<track>` elements provide text tracks (captions, subtitles, descriptions) for video content. These are the standard mechanism for text-based access to video information.
- **What It Does NOT Establish**: That all AI systems require text tracks.
- **Evidence Type**: SOURCE-DERIVED FACT

### REF-F5: W3C WAI — Making Audio and Video Accessible
- **Organization**: W3C
- **URL**: https://www.w3.org/WAI/media/av/
- **Mechanism Supported**: lock-in (F-003)
- **Claim Supported**: Videos need captions and transcripts for accessibility. Provides guidelines for text equivalents of multimedia content.
- **What It Does NOT Establish**: AI-specific requirements.
- **Evidence Type**: SOURCE-DERIVED FACT

### REF-F6: W3C — PDF Accessibility Techniques
- **Organization**: W3C
- **URL**: https://www.w3.org/WAI/WCAG22/Techniques/#pdf
- **Mechanism Supported**: lock-in (F-002)
- **Claim Supported**: PDF content should have HTML alternatives for accessibility. PDF is a separate document format not directly parseable from webpage HTML.
- **What It Does NOT Establish**: Whether search engines or AI systems index linked PDFs effectively.
- **Evidence Type**: SOURCE-DERIVED FACT

### REF-F7: Google Search Central — Image Best Practices
- **Organization**: Google
- **URL**: https://developers.google.com/search/docs/appearance/google-images
- **Mechanism Supported**: lock-in (F-001)
- **Claim Supported**: Google uses alt text and surrounding context to understand image content. Descriptive alt text helps search engines and AI systems interpret images.
- **What It Does NOT Establish**: That images without alt text are invisible to all AI systems.
- **Evidence Type**: SOURCE-DERIVED FACT (Google-specific)

### REF-F8: Google Search Central — Indexable File Types
- **Organization**: Google
- **URL**: https://developers.google.com/search/docs/crawling-indexing/indexable-file-types
- **Mechanism Supported**: lock-in (F-002)
- **Claim Supported**: Google can index PDF content separately, but this is distinct from webpage HTML content.
- **What It Does NOT Establish**: How AI assistants handle linked PDFs when answering questions.
- **Evidence Type**: SOURCE-DERIVED FACT (Google-specific)

## Tier 1: Round 3 Handbook

### REF-F9: Round 3 Handbook — Section F
- **Organization**: Adobe University Hackathon
- **Mechanism Supported**: lock-in (F-001, F-002, F-003)
- **Claim Supported**: "when the real substance...isn't available as readable text — for example, when it's carried by something a summarizer can't read...the important part can simply disappear."
- **What It Does NOT Establish**: Specific media type checks or thresholds.
- **Evidence Type**: SOURCE-DERIVED FACT
