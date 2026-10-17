/** Integer VND with Vietnamese grouping, e.g. 40000 -> "40.000 ₫". */
export function formatVnd(amount: number): string {
  return `${amount.toLocaleString('vi-VN')} ₫`
}
