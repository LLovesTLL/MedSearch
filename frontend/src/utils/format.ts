export function formatAuthors(authors: string[]): string {
  if (!authors || authors.length === 0) {
    return '未知作者'
  }
  const shown = authors.slice(0, 3).join(', ')
  return authors.length > 3 ? `${shown}...` : shown
}

export function pubmedUrl(pmid: string): string {
  return `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`
}