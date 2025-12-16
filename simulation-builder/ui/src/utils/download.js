
/**
 * Triggers a download of a Blob object.
 * @param {Blob} blob - The blob to download.
 * @param {string} filename - The name of the file.
 */
export const downloadBlob = (blob, filename) => {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
};

/**
 * Downloads a text string as a file.
 * @param {string} text - The text content.
 * @param {string} filename - The filename (e.g., 'config.txt').
 */
export const downloadText = (text, filename) => {
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    downloadBlob(blob, filename);
};

/**
 * Downloads an array of objects as a CSV file.
 * @param {Array<Object>} data - The data array.
 * @param {string} filename - The filename (e.g., 'data.csv').
 */
export const downloadCSV = (data, filename) => {
    if (!data || !data.length) return;
    
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => {
            const val = row[header];
            // Handle strings with commas or quotes
            if (typeof val === 'string' && (val.includes(',') || val.includes('"'))) {
                return `"${val.replace(/"/g, '""')}"`;
            }
            return val;
        }).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' });
    downloadBlob(blob, filename);
};

/**
 * Converts an SVG element to a PNG and downloads it.
 * @param {SVGElement} svgElement - The SVG DOM element.
 * @param {string} filename - The filename (e.g., 'chart.png').
 * @param {number} scale - Scale factor for higher resolution (default 2).
 */
export const downloadSVGAsPNG = (svgElement, filename, scale = 4) => {
    if (!svgElement) {
        console.error("SVG element not found");
        return;
    }
    console.log(svgElement);
    // 1. Clone the node first
    const clone = svgElement.cloneNode(true);
    
    // 2. Determine dimensions
    let width, height;
    const viewBox = svgElement.getAttribute('viewBox');
    
    if (viewBox) {
        // Handle both space and comma separators
        const parts = viewBox.split(/[\s,]+/).filter(Boolean).map(Number);
        if (parts.length === 4) {
            width = parts[2];
            height = parts[3];
        }
    }
    
    // Fallback if viewBox is missing or parsing failed
    if (!width || !height) {
        const rect = svgElement.getBoundingClientRect();
        width = rect.width;
        height = rect.height;
        // Add viewBox if missing to define the coordinate system
        if (!clone.getAttribute('viewBox')) {
             clone.setAttribute('viewBox', `0 0 ${width} ${height}`);
        }
    }

    // 3. Set explicit width/height on clone to match its internal coordinate system
    clone.setAttribute('width', width);
    clone.setAttribute('height', height);
    
    // 4. Styling
    clone.style.overflow = 'visible';
    clone.style.backgroundColor = '#ffffff';

    // 5. Serialize
    const serializer = new XMLSerializer();
    let svgString = serializer.serializeToString(clone);

    if (!svgString.match(/^<svg[^>]+xmlns="http\:\/\/www\.w3\.org\/2000\/svg"/)) {
        svgString = svgString.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
    }

    const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(svgBlob);

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    const img = new Image();
    img.onload = () => {
        // 6. Set canvas to scaled dimensions
        canvas.width = width * scale;
        canvas.height = height * scale;
        
        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // 7. Draw image scaled
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(blob => {
            downloadBlob(blob, filename);
            URL.revokeObjectURL(url);
        }, 'image/png');
    };
    img.src = url;
};
