# OGM Viewer Endpoints

This document describes the new API endpoints for embedding the OpenGeoMetadata (OGM) viewer in your applications.

## Overview

The OGM viewer endpoints provide multiple ways to integrate the [ogm-viewer](https://github.com/OpenGeoMetadata/ogm-viewer) web component with your API. The viewer is a powerful tool for displaying geospatial metadata records with interactive maps and metadata panels.

## Available Endpoints

### 1. Viewer Page (`/api/v1/resources/{id}/viewer`)

Serves a complete HTML page with the embedded OGM viewer.

**URL:** `GET /api/v1/resources/{id}/viewer`

**Parameters:**
- `id` (path): Resource ID
- `theme` (query): Theme preference - `light`, `dark`, or `auto` (default: `auto`)
- `embed` (query): Enable embedded mode for iframe usage - `true` or `false` (default: `false`)

**Example:**
```bash
curl "http://localhost:8000/api/v1/resources/your-resource-id/viewer?theme=dark&embed=true"
```

**Response:** Complete HTML page with embedded viewer

### 2. Embed Snippet (`/api/v1/resources/{id}/viewer/embed`)

Returns an HTML snippet for embedding the viewer in an iframe.

**URL:** `GET /api/v1/resources/{id}/viewer/embed`

**Parameters:**
- `id` (path): Resource ID
- `theme` (query): Theme preference - `light`, `dark`, or `auto` (default: `auto`)
- `height` (query): Height of the embedded viewer (default: `600px`)
- `width` (query): Width of the embedded viewer (default: `100%`)

**Example:**
```bash
curl "http://localhost:8000/api/v1/resources/your-resource-id/viewer/embed?height=800px&width=90%"
```

**Response:** HTML snippet with iframe

### 3. Viewer Configuration (`/api/v1/resources/{id}/viewer/config`)

Returns configuration information for integrating the viewer.

**URL:** `GET /api/v1/resources/{id}/viewer/config`

**Parameters:**
- `id` (path): Resource ID

**Example:**
```bash
curl "http://localhost:8000/api/v1/resources/your-resource-id/viewer/config"
```

**Response:**
```json
{
  "record_url": "http://localhost:8000/api/v1/resources/your-resource-id/ogm",
  "viewer_url": "http://localhost:8000/api/v1/resources/your-resource-id/viewer",
  "embed_url": "http://localhost:8000/api/v1/resources/your-resource-id/viewer/embed",
  "embed_html": "<iframe src=\"http://localhost:8000/api/v1/resources/your-resource-id/viewer?embed=true\" width=\"100%\" height=\"600px\" frameborder=\"0\"></iframe>",
  "web_component_usage": "<ogm-viewer record-url=\"http://localhost:8000/api/v1/resources/your-resource-id/ogm\"></ogm-viewer>",
  "script_tag": "<script type=\"module\" src=\"https://unpkg.com/ogm-viewer\"></script>"
}
```

## Integration Methods

### Method 1: Direct iframe Embedding

The simplest way to embed the viewer is using an iframe:

```html
<iframe 
    src="http://localhost:8000/api/v1/resources/your-resource-id/viewer?embed=true" 
    width="100%" 
    height="600px" 
    frameborder="0"
    title="OGM Viewer">
</iframe>
```

### Method 2: Web Component Usage

For more control, use the OGM viewer as a web component:

```html
<!-- Load the web component -->
<script type="module" src="https://unpkg.com/ogm-viewer"></script>

<!-- Use the component -->
<ogm-viewer 
    record-url="http://localhost:8000/api/v1/resources/your-resource-id/ogm"
    theme="dark">
</ogm-viewer>
```

### Method 3: Dynamic Integration

Load the embed snippet dynamically:

```javascript
async function embedViewer(resourceId) {
    const response = await fetch(`/api/v1/resources/${resourceId}/viewer/embed?height=800px`);
    const html = await response.text();
    document.getElementById('viewer-container').innerHTML = html;
}
```

### Method 4: Configuration-Based Integration

Get configuration and build your own integration:

```javascript
async function getViewerConfig(resourceId) {
    const response = await fetch(`/api/v1/resources/${resourceId}/viewer/config`);
    const config = await response.json();
    
    // Use config.embed_html, config.web_component_usage, etc.
    console.log('Embed HTML:', config.embed_html);
    console.log('Web Component Usage:', config.web_component_usage);
}
```

## Features

### Theme Support

The viewer supports three theme modes:

- **`light`**: Light theme
- **`dark`**: Dark theme  
- **`auto`**: Automatically matches system preference (default)

### Responsive Design

The viewer is fully responsive and works on desktop and mobile devices.

### Interactive Features

- Interactive map with zoom and pan
- Metadata sidebar with record information
- Layer opacity controls
- Download options
- Citation information

## Examples

See `examples/viewer_example.html` for comprehensive examples of all integration methods.

## Browser Compatibility

The OGM viewer uses modern web standards and requires:

- ES6 modules support
- Web Components support
- Fetch API support

**Supported browsers:**
- Chrome 67+
- Firefox 63+
- Safari 11.1+
- Edge 79+

## CORS Considerations

The viewer endpoints are designed to work with the permissive CORS settings we've configured. The viewer can be embedded in iframes from any domain.

## Performance

- The viewer loads the OGM web component from CDN (unpkg.com)
- Record data is fetched from your API's `/ogm` endpoint
- The viewer includes built-in caching for map tiles and data

## Troubleshooting

### Common Issues

1. **Viewer not loading**: Check that the resource ID exists and the `/ogm` endpoint returns valid data
2. **CORS errors**: Ensure your API has permissive CORS settings
3. **Theme not applying**: Verify the theme parameter is one of: `light`, `dark`, or `auto`
4. **Iframe not displaying**: Check that the embed parameter is set to `true`

### Debug Mode

Enable browser developer tools to see any JavaScript errors or network issues.

## Related Endpoints

- `/api/v1/resources/{id}` - Full JSON:API resource
- `/api/v1/resources/{id}/ogm` - Raw Aardvark record (used by viewer)
- `/api/v1/thumbnails/{image_hash}` - Thumbnail images
