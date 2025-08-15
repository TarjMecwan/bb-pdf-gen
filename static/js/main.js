// Show alert message
function showAlert(message, type = 'info') {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    
    // Add message and close button
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to the page
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, 5000);
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    const sizeInMB = bytes / (k * k);
    const sizeInGB = sizeInMB / k;
    
    if (i < 2) {
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    } else if (i === 2) { // MB
        return sizeInMB.toFixed(2) + ' MB';
    } else { // GB or larger
        return sizeInMB.toFixed(2) + ' MB (' + sizeInGB.toFixed(2) + ' GB)';
    }
}

// Handle file selection
function handleFileSelect(file) {
    const fileName = file.name;
    const fileSize = file.size;
    
    // Update file info
    document.getElementById('fileName').textContent = fileName;
    document.getElementById('fileSize').textContent = formatFileSize(fileSize);
    
    // Show file info
    document.getElementById('fileInfo').classList.remove('d-none');
    
    // Update preview
    updatePreview();
}

// Pagination state
let currentPage = 1;
let totalPages = 1;

// Update page content based on current page
function updatePageContent() {
    const previewMarkup = document.querySelector('.preview-markup');
    previewMarkup.innerHTML = '';
    
    // Build markups display based on new controls
    const textEnabled = document.getElementById('textCheck')?.checked;
    const shapesEnabled = document.getElementById('shapesCheck')?.checked;
    let markups = [];
    if (textEnabled) markups.push('Text');
    if (shapesEnabled) {
        const shapeTypes = Array.from(document.querySelectorAll('#shapeOptions input[name="shapeType"]:checked'))
            .map(el => ({ box: 'Box', cloud: 'Cloud', pen: 'Vector Pen' }[el.value] || el.value));
        if (shapeTypes.length) {
            markups.push(`Shapes (${shapeTypes.join(', ')})`);
        } else {
            markups.push('Shapes');
        }
    }
    markups = markups.join(', ');
    
    // Add page number indicator
    const pageIndicator = document.createElement('div');
    pageIndicator.className = 'page-indicator';
    pageIndicator.textContent = `Page ${currentPage}`;
    pageIndicator.style.fontWeight = 'bold';
    pageIndicator.style.marginBottom = '10px';
    previewMarkup.appendChild(pageIndicator);
    
    // Add content based on markups
    if (markups.includes('Text')) {
        const text = document.createElement('div');
        text.className = 'preview-text-item';
        text.textContent = `Sample text content for page ${currentPage}`;
        text.style.borderBottom = '1px solid #dee2e6';
        text.style.padding = '5px';
        text.style.margin = '3px 0';
        previewMarkup.appendChild(text);
    }
    
    if (markups.includes('Shapes')) {
        const shape = document.createElement('div');
        shape.className = 'preview-shape';
        shape.style.width = `${40 + (currentPage * 5)}px`; // Vary size by page
        shape.style.height = `${30 + (currentPage * 3)}px`;
        shape.style.border = '2px solid #0283DB';
        shape.style.margin = '10px auto';
        shape.style.borderRadius = '4px';
        previewMarkup.appendChild(shape);
    }
    
    if (markups === '') {
        previewMarkup.textContent = 'No markups selected';
    }
    
    // Update navigation buttons
    document.getElementById('prevPage').disabled = currentPage <= 1;
    document.getElementById('nextPage').disabled = currentPage >= totalPages;
    document.getElementById('currentPage').textContent = currentPage;
}

// PDF.js preview helpers (kept for future use but not auto-invoked)
let pdfjsDoc = null;
function loadPdfJsPreviewFromBlob(blob) {
    const url = URL.createObjectURL(blob);
    window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.2.67/pdf.worker.min.js';
    window.pdfjsLib.getDocument(url).promise.then(function(pdfDoc_) {
        pdfjsDoc = pdfDoc_;
        totalPages = pdfjsDoc.numPages;
        renderPdfJsPage(currentPage);
    }).catch(function(error) {
        pdfjsDoc = null;
        renderPdfJsPage(null, error);
    });
}
function renderPdfJsPage(pageNum, error) {
    const canvas = document.getElementById('pdfPreviewCanvas');
    if (!canvas) {
        // Canvas removed in favor of iframe preview. Do nothing.
        return;
    }
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (error) {
        ctx.font = '16px sans-serif';
        ctx.fillStyle = '#d9534f';
        ctx.fillText('Could not load PDF preview.', 10, 50);
        return;
    }
    if (!pdfjsDoc) {
        ctx.font = '16px sans-serif';
        ctx.fillStyle = '#adb5bd';
        ctx.fillText('No PDF loaded. Generate a PDF to preview.', 10, 50);
        return;
    }
    if (!pageNum) pageNum = 1;
    pdfjsDoc.getPage(pageNum).then(function(page) {
        const viewport = page.getViewport({ scale: 1.5 });
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        const renderContext = {
            canvasContext: ctx,
            viewport: viewport
        };
        page.render(renderContext);
    });
}

// Format helpers for dates
function getTodayISO() {
    const d = new Date();
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    return `${d.getFullYear()}-${mm}-${dd}`;
}

function formatISODateNice(iso) {
    try {
        // Parse as LOCAL date to avoid UTC timezone shifting for 'YYYY-MM-DD'
        const parts = iso.split('-');
        if (parts.length !== 3) return iso;
        const y = Number(parts[0]);
        const m = Number(parts[1]);
        const d = Number(parts[2]);
        if (!y || !m || !d) return iso;
        const dt = new Date(y, m - 1, d); // Local time
        if (isNaN(dt.getTime())) return iso;
        return dt.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    } catch (_) {
        return iso;
    }
}

// Update preview panel
function updatePreview() {
    const targetSize = document.getElementById('targetSize').value;
    totalPages = parseInt(document.getElementById('pageCount').value) || 1;
    const fileNameInput = document.getElementById('fileName');
    const baseFileName = fileNameInput.value.trim() || 'bluebeam_document';
    const checkboxes = document.querySelectorAll('input[name="markup_types"]:checked');
    const markups = Array.from(checkboxes).map(cb => 
        cb.value.charAt(0).toUpperCase() + cb.value.slice(1)
    ).join(', ');

    // Update preview elements
    const sizeInMB = parseFloat(targetSize);
    const sizeInGB = sizeInMB / 1024;
    const sizeDisplay = sizeInMB < 1024 ? 
        `${sizeInMB.toFixed(2)} MB` : 
        `${sizeInMB.toFixed(2)} MB (${sizeInGB.toFixed(2)} GB)`;
    
    document.getElementById('previewFileSize').textContent = sizeDisplay;
    document.getElementById('previewPages').textContent = totalPages;
    document.getElementById('previewMarkups').textContent = markups || 'None';
    document.getElementById('totalPages').textContent = totalPages;
    
    // Update filename in preview
    document.getElementById('previewFileName').textContent = `${baseFileName}.pdf`;
    // Update last updated date in preview (defaults to today)
    const modifiedDateInput = document.getElementById('modifiedDate');
    const iso = (modifiedDateInput && modifiedDateInput.value) ? modifiedDateInput.value : getTodayISO();
    const lastUpdatedEl = document.getElementById('previewLastUpdated');
    if (lastUpdatedEl) lastUpdatedEl.textContent = formatISODateNice(iso);
    
    // Reset to first page if current page exceeds total pages
    if (currentPage > totalPages) {
        currentPage = 1;
    }
    
    updatePageContent();
}

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('pdfForm');
    const generateBtn = document.getElementById('generateBtn');
    
    const downloadLink = document.getElementById('downloadLink');
    const spinner = generateBtn.querySelector('.spinner-border');
    const prevPageBtn = document.getElementById('prevPage');
    const nextPageBtn = document.getElementById('nextPage');
    
    // Add event listeners for form changes
    const formInputs = form.querySelectorAll('input, textarea, select');
    formInputs.forEach(input => {
        input.addEventListener('change', function() {
            // If page count changes, reset to first page
            if (this.id === 'pageCount') {
                currentPage = 1;
            }
            updatePreview();
        });
        input.addEventListener('input', function() {
            // If page count changes, reset to first page
            if (this.id === 'pageCount') {
                currentPage = 1;
            }
            updatePreview();
        });
    });
    
    // Toggle annotation box visibility (Text markup)
    const textCheck = document.getElementById('textCheck');
    const annotationBox = document.getElementById('annotationBox');
    if (textCheck && annotationBox) {
        const syncAnnotationBox = () => {
            annotationBox.classList.toggle('d-none', !textCheck.checked);
        };
        textCheck.addEventListener('change', syncAnnotationBox);
        syncAnnotationBox();
    }

    // Toggle shape options visibility
    const shapesCheck = document.getElementById('shapesCheck');
    const shapeOptions = document.getElementById('shapeOptions');
    if (shapesCheck && shapeOptions) {
        const syncShapeOptions = () => {
            shapeOptions.classList.toggle('d-none', !shapesCheck.checked);
        };
        shapesCheck.addEventListener('change', syncShapeOptions);
        syncShapeOptions();
    }

    // Add event listeners for pagination
    prevPageBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            updatePageContent();
            renderPdfJsPage(currentPage);
        }
    });
    
    nextPageBtn.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            updatePageContent();
            renderPdfJsPage(currentPage);
        }
    });
    
    // Default the modified date to today if empty
    const modifiedDateInput = document.getElementById('modifiedDate');
    if (modifiedDateInput && !modifiedDateInput.value) {
        modifiedDateInput.value = getTodayISO();
    }
    // Initialize preview
    updatePreview();

    // Do not auto-load any PDF.js preview; iframe in the template shows the current uploads PDF
    
    // Handle sample markdown button
    const sampleMarkdownBtn = document.getElementById('sampleMarkdown');
    if (sampleMarkdownBtn) {
        sampleMarkdownBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const sampleText = `Electrical Box Here

Main Water Valve

HVAC Unit Location

Load-Bearing Wall

Emergency Exit Door

Access Panel

Cable Routing Path

Fuse Box

Fire Alarm Sensor

Light Switch

Ceiling Height: 10 ft

Plumbing Pipe Route

Ventilation Ducts

Sprinkler System Zone 1

Data Network Outlet

Concrete Foundation

Solar Panel Mounting

Smoke Detector

Gas Meter Location

Structural Support Beam`;

            const markdownContent = document.getElementById('markdownContent');
            if (markdownContent) {
                markdownContent.value = sampleText;
            }
        });
    }
    
    // Markdown preview
    function updateMarkdownPreview() {
        const markdownContent = document.getElementById('markdownContent');
        const preview = document.getElementById('markdownPreview');
        
        if (markdownContent && preview) {
            // Simple markdown to HTML conversion
            let html = markdownContent.value
                .replace(/^# (.*$)/gm, '<h1>$1</h1>')
                .replace(/^## (.*$)/gm, '<h2>$1</h2>')
                .replace(/^### (.*$)/gm, '<h3>$1</h3>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
                .replace(/^\- (.*$)/gm, '<li>$1</li>')
                .replace(/^> (.*$)/gm, '<blockquote>$1</blockquote>')
                .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
                .replace(/\n\n/g, '<br><br>')
                .replace(/\n/g, '<br>');
            
            // Wrap list items in ul
            html = html.replace(/(<li>.*?<\/li>)/g, '<ul>$1</ul>');
            
            preview.innerHTML = html || '<p class="text-muted">Markdown preview will appear here...</p>';
        }
    }
    
    // Update preview when markdown changes
    const markdownContent = document.getElementById('markdownContent');
    if (markdownContent) {
        markdownContent.addEventListener('input', updateMarkdownPreview);
    }
    
    // Form submission
    // State for generated PDF
    let generatedPdfBlob = null;
    let generatedPdfFilename = null;
    const downloadBtn = document.getElementById('downloadBtn');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const defaultPdf = document.getElementById('defaultPdf');
        const outputFileName = (document.getElementById('fileName').value || 'generated_document').trim();
        const markdownContent = document.getElementById('markdownContent');

        if (!defaultPdf) {
            showAlert('No default PDF is available. Please add a PDF to the uploads folder.', 'danger');
            return;
        }
        if (!outputFileName) {
            showAlert('Please enter a file name for the generated PDF.', 'warning');
            return;
        }
        if (!markdownContent || markdownContent.value.trim() === '') {
            showAlert('No annotations entered. The PDF will be generated without bubbles.', 'info');
        }

        const formData = new FormData();
        formData.append('fileName', outputFileName);
        const targetSizeInput = document.getElementById('targetSize');
        formData.append('targetSize', targetSizeInput && targetSizeInput.value ? targetSizeInput.value : '10');
        const pageCountInput = document.getElementById('pageCount');
        formData.append('pageCount', pageCountInput && pageCountInput.value ? pageCountInput.value : '1');
        formData.append('markdown', markdownContent ? markdownContent.value : '');
        // Add optional modified date (YYYY-MM-DD)
        const modifiedDateInput = document.getElementById('modifiedDate');
        if (modifiedDateInput && modifiedDateInput.value) {
            formData.append('modifiedDate', modifiedDateInput.value);
        }
        // Add markup selections
        const textEnabled = document.getElementById('textCheck')?.checked ? 'true' : 'false';
        const shapesEnabled = document.getElementById('shapesCheck')?.checked ? 'true' : 'false';
        formData.append('textEnabled', textEnabled);
        formData.append('shapesEnabled', shapesEnabled);
        const shapeTypes = Array.from(document.querySelectorAll('#shapeOptions input[name="shapeType"]:checked')).map(el => el.value);
        if (shapeTypes.length) {
            formData.append('shapeTypes', shapeTypes.join(','));
        }
        formData.append('useDefault', 'true');

        const generateBtn = document.getElementById('generateBtn');
        const originalBtnText = generateBtn.innerHTML;
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';

        try {
            const response = await fetch('/generate', { method: 'POST', body: formData });
            if (!response.ok) {
                const errorText = await response.text();
                let errorMessage = 'Failed to generate PDF';
                try { errorMessage = (JSON.parse(errorText).error) || errorMessage; } catch(_) { errorMessage = errorText || errorMessage; }
                throw new Error(errorMessage);
            }

            // Determine filename
            let filename = outputFileName.endsWith('.pdf') ? outputFileName : `${outputFileName}.pdf`;
            const cd = response.headers.get('content-disposition');
            if (cd) {
                const m = cd.match(/filename="?([^\";]+)"?/);
                if (m && m[1]) filename = m[1];
            }

            const blob = await response.blob();
            generatedPdfBlob = blob;
            generatedPdfFilename = filename;
            downloadBtn.disabled = false;

            // Do not alter the preview; keep showing the current uploads PDF in the iframe

            showAlert('PDF generated successfully. You can download it now.', 'success');
        } catch (err) {
            showAlert(err.message || 'An unexpected error occurred while generating the PDF.', 'danger');
        } finally {
            generateBtn.disabled = false;
            generateBtn.innerHTML = originalBtnText;
        }
    });

    // Download button handler
    if (downloadBtn) {
        downloadBtn.addEventListener('click', function() {
            if (!generatedPdfBlob) {
                showAlert('No PDF available for download. Please generate one first.', 'warning');
                return;
            }
            const url = URL.createObjectURL(generatedPdfBlob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = generatedPdfFilename || 'generated_document.pdf';
            document.body.appendChild(a);
            a.click();
            setTimeout(() => {
                URL.revokeObjectURL(url);
                document.body.removeChild(a);
            }, 100);
        });
    }
});
