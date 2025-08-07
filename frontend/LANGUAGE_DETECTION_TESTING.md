# Language Auto-Detection Test Guide

## Testing Language Auto-Detection in Sonicus

The Sonicus platform now automatically detects user language preferences and falls back to English (USA) when necessary.

### How Auto-Detection Works:

1. **Query Parameter**: `?lng=en-GB` (highest priority)
2. **Stored Cookie**: Previous language choice cached
3. **Local Storage**: User's saved language preference
4. **Browser Language**: `navigator.language` detection
5. **HTML Lang Tag**: Document language attribute

### Test URLs:

```
# Force English (US)
http://localhost:3000?lng=en-US

# Force English (UK) 
http://localhost:3000?lng=en-GB

# Force Spanish
http://localhost:3000?lng=es

# Force Portuguese (Brazil)
http://localhost:3000?lng=pt-BR

# Force Portuguese (Portugal)
http://localhost:3000?lng=pt-PT

# Force French
http://localhost:3000?lng=fr

# Force German
http://localhost:3000?lng=de

# Test unsupported language (should fallback to en-US)
http://localhost:3000?lng=zh-CN

# Clear stored preferences and test auto-detection
http://localhost:3000?lng=clear
```

### Detection Logic:

1. **English Detection**:
   - `en-US`, `en-us` → American English
   - `en-GB`, `en-gb`, `en-UK` → British English
   - `en` (generic) → Checks browser for region, defaults to `en-US`

2. **Portuguese Detection**:
   - `pt-BR`, `pt-br` → Brazilian Portuguese
   - `pt-PT`, `pt-pt` → European Portuguese  
   - `pt` (generic) → Checks browser for region, defaults to `pt-BR`

3. **Other Languages**:
   - `es*` → Spanish
   - `fr*` → French
   - `de*` → German

4. **Fallback**:
   - Any unsupported language → English (USA)
   - Detection failure → English (USA)

### Browser Console Logging:

When in development mode, check the browser console for:
- `Detected language: [code]`
- `Full browser language: [code]`
- `i18n initialized with language: [code]`
- `Language changed to: [code]`

### Manual Testing:

1. Change browser language settings
2. Clear localStorage: `localStorage.removeItem('i18nextLng')`
3. Clear cookies and reload
4. Test with different URL parameters
5. Verify language switcher updates correctly
