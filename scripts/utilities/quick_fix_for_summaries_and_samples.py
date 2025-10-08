#!/usr/bin/env python3
"""
Quick fix for AI summary issues and sample viewer
"""

# Add this to your existing working main.py file


# 1. Enhanced summary processing function
def process_ai_summary_safely(ai_summary, geo_id, original_summary):
    """Process AI summary with generic detection"""

    # Check for generic indicators
    generic_indicators = [
        "GSE297209",
        "GSE284759",
        "GSE289246",
        "does not specifically address",
        "does not directly address",
    ]

    if ai_summary and isinstance(ai_summary, dict):
        # Extract readable text
        display_summary = (
            ai_summary.get("overview")
            or ai_summary.get("methodology")
            or ai_summary.get("significance")
            or str(ai_summary)
        )

        # Check if summary is generic
        is_generic = any(indicator in str(ai_summary) for indicator in generic_indicators)

        # Check if mentions wrong GEO ID
        for indicator in generic_indicators[:3]:  # GEO IDs
            if indicator in display_summary and geo_id != indicator and geo_id != "unknown":
                is_generic = True
                break

        if is_generic:
            print(f"Generic AI summary detected for {geo_id}, using original")
            return original_summary, None
        else:
            return display_summary, ai_summary
    else:
        return original_summary, None


# 2. Sample API endpoint (add this to your FastAPI app)
"""
@app.get("/api/samples/{geo_id}")
async def get_samples(geo_id: str):
    try:
        # Example: Get samples from GEO or your internal database
        samples = []

        # FOR YOUR INTERNAL DATABASE - REPLACE THIS SECTION:
        # if geo_id in your_internal_database:
        #     samples = query_internal_database(geo_id)

        # FOR NOW: Return GEO-based sample structure
        sample_template = {
            "geo_id": geo_id,
            "samples": [
                {
                    "sample_id": f"GSM{i+1000000}",
                    "sample_name": f"Sample_{i+1}",
                    "tissue_type": "Brain" if "brain" in geo_id.lower() else "Unknown",
                    "treatment": "Control" if i % 2 == 0 else "Treatment",
                    "platform": "Illumina HiSeq",
                    "source": "internal" if geo_id != "unknown" else "unavailable"
                }
                for i in range(min(10, 20))  # Limit samples for demo
            ],
            "total_count": 20,
            "status": "success"
        }

        return JSONResponse(sample_template)
    except Exception as e:
        return JSONResponse({"error": str(e), "status": "error"}, status_code=500)
"""

# 3. Frontend JavaScript for sample viewer (add to your HTML template)
sample_viewer_js = """
<script>
// Add this to your existing script section

async function showSamples(geoId) {
    try {
        const response = await fetch(`/api/samples/${geoId}`);
        const data = await response.json();

        if (data.status === 'success') {
            displaySamplesModal(data);
        } else {
            alert('Sample data not available for this dataset');
        }
    } catch (error) {
        alert('Error loading samples: ' + error.message);
    }
}

function displaySamplesModal(data) {
    // Create modal if it doesn't exist
    let modal = document.getElementById('samplesModal');
    if (!modal) {
        modal = createSamplesModal();
        document.body.appendChild(modal);
    }

    // Populate modal content
    const modalContent = `
        <div class="modal-header">
            <h2>📋 Samples for ${data.geo_id}</h2>
            <span class="close" onclick="closeSamplesModal()">&times;</span>
        </div>
        <div class="modal-body">
            <p><strong>Total Samples:</strong> ${data.total_count}</p>
            <table class="samples-table">
                <thead>
                    <tr>
                        <th>Sample ID</th>
                        <th>Name</th>
                        <th>Tissue</th>
                        <th>Treatment</th>
                        <th>Platform</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.samples.map(sample => `
                        <tr>
                            <td>${sample.sample_id}</td>
                            <td>${sample.sample_name}</td>
                            <td>${sample.tissue_type}</td>
                            <td>${sample.treatment}</td>
                            <td>${sample.platform}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
        <div class="modal-footer">
            <button onclick="closeSamplesModal()">Close</button>
        </div>
    `;

    modal.innerHTML = modalContent;
    modal.style.display = 'block';
}

function createSamplesModal() {
    const modal = document.createElement('div');
    modal.id = 'samplesModal';
    modal.className = 'modal';
    modal.style.cssText = `
        display: none;
        position: fixed;
        z-index: 1000;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0.5);
    `;

    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background-color: white;
        margin: 5% auto;
        padding: 20px;
        border-radius: 10px;
        width: 80%;
        max-width: 800px;
        max-height: 80vh;
        overflow-y: auto;
    `;

    modal.appendChild(modalContent);
    return modal;
}

function closeSamplesModal() {
    document.getElementById('samplesModal').style.display = 'none';
}

// Update the displayResults function to include sample buttons
function displayResults(data) {
    const results = document.getElementById('results');

    if (data.results && data.results.length > 0) {
        let html = `<div class="success">✅ Found ${data.results.length} datasets</div>`;

        data.results.forEach(result => {
            const aiIndicator = result.ai_enhanced ?
                '<span style="color: #28a745; font-weight: bold;">🤖 AI Enhanced</span> | ' : '';
            const samplesBtn = result.id !== 'unknown' ?
                `<button class="btn-samples" onclick="showSamples('${result.id}')"
                         style="background: #28a745; color: white; border: none; padding: 5px 10px;
                                border-radius: 5px; margin-left: 10px; cursor: pointer;">
                    📋 View Samples
                </button>` : '';

            html += `
                <div class="result-item">
                    <div class="result-title">${result.title}</div>
                    <div class="result-meta">
                        ${aiIndicator}ID: ${result.id} |
                        Organism: ${result.organism || 'Unknown'} |
                        Samples: ${result.sample_count || 'Unknown'}
                        ${samplesBtn}
                    </div>
                    <div class="result-summary">${result.summary}</div>
                </div>
            `;
        });

        results.innerHTML = html;
    } else {
        results.innerHTML = '<div class="error">No datasets found for your query. Try different keywords.</div>';
    }
}
</script>
"""

print("Quick fix code ready!")
print("1. Use process_ai_summary_safely() function in your backend")
print("2. Add the sample API endpoint")
print("3. Replace your displayResults JavaScript with the enhanced version")
print("4. Add the sample viewer JavaScript")

# Example usage in your search endpoint:
"""
# In your search processing loop:
for i, result in enumerate(results.metadata[:max_results]):
    ai_summary = individual_summaries[i].get('summary') if i < len(individual_summaries) else None
    original_summary = result.get('summary', result.get('description', 'No description available'))

    # Use the safe processing function
    display_summary, processed_ai_summary = process_ai_summary_safely(
        ai_summary, result.get('id', 'unknown'), original_summary
    )

    processed_results.append({
        "id": result.get('id', 'unknown'),
        "title": result.get('title', 'No title'),
        "summary": display_summary,
        "ai_enhanced": bool(processed_ai_summary),
        # ... other fields
    })
"""
