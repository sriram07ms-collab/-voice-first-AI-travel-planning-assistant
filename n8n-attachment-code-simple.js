// Option 1: Simplified (Recommended)
={{ (() => { try { if ($binary && $binary.data && $binary.data.data) { return [{ name: 'itinerary.pdf', data: $binary.data.data, type: 'application/pdf' }]; } const pdfNode = $('Generate PDF'); if (pdfNode && pdfNode.item && pdfNode.item.binary && pdfNode.item.binary.data) { const binaryData = pdfNode.item.binary.data.data || pdfNode.item.binary.data; return [{ name: 'itinerary.pdf', data: binaryData, type: 'application/pdf' }]; } if ($binary && $binary.data) { return [{ name: 'itinerary.pdf', data: $binary.data, type: 'application/pdf' }]; } if ($input && $input.item && $input.item.binary && $input.item.binary.data) { const inputBinary = $input.item.binary.data.data || $input.item.binary.data; return [{ name: 'itinerary.pdf', data: inputBinary, type: 'application/pdf' }]; } console.log('WARNING: PDF binary data not found'); return []; } catch (error) { console.log('Error:', error.message); return []; } })() }}

// Option 2: Minimal (If Option 1 fails)
={{ $binary && $binary.data && $binary.data.data ? [{ name: 'itinerary.pdf', data: $binary.data.data, type: 'application/pdf' }] : ($binary && $binary.data ? [{ name: 'itinerary.pdf', data: $binary.data, type: 'application/pdf' }] : []) }}

// Option 3: Most Basic (If both above fail)
={{ $binary && $binary.data ? [{ name: 'itinerary.pdf', data: $binary.data.data || $binary.data, type: 'application/pdf' }] : [] }}
