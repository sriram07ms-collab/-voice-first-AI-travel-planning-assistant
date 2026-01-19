// CORRECTED CODE - Using "results.pdf" as the filename

// Option 1: Simplest (Recommended - try this first)
={{ $binary && $binary.data ? [{ name: 'results.pdf', data: $binary.data.data || $binary.data, type: 'application/pdf' }] : [] }}

// Option 2: With more fallbacks (if Option 1 doesn't work)
={{ $binary && $binary.data && $binary.data.data ? [{ name: 'results.pdf', data: $binary.data.data, type: 'application/pdf' }] : ($binary && $binary.data ? [{ name: 'results.pdf', data: $binary.data, type: 'application/pdf' }] : []) }}

// Option 3: Full version with all fallbacks (if both above fail)
={{ (() => { try { if ($binary && $binary.data && $binary.data.data) { return [{ name: 'results.pdf', data: $binary.data.data, type: 'application/pdf' }]; } const pdfNode = $('Generate PDF'); if (pdfNode && pdfNode.item && pdfNode.item.binary && pdfNode.item.binary.data) { const binaryData = pdfNode.item.binary.data.data || pdfNode.item.binary.data; return [{ name: 'results.pdf', data: binaryData, type: 'application/pdf' }]; } if ($binary && $binary.data) { return [{ name: 'results.pdf', data: $binary.data, type: 'application/pdf' }]; } if ($input && $input.item && $input.item.binary && $input.item.binary.data) { const inputBinary = $input.item.binary.data.data || $input.item.binary.data; return [{ name: 'results.pdf', data: inputBinary, type: 'application/pdf' }]; } return []; } catch (error) { return []; } })() }}
