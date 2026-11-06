import { useState } from 'react'
import { Coffee } from 'lucide-react'

import { cn } from '@/lib/utils'

/**
 * Product photo, or a neutral placeholder when the product has no image yet or the file can't be loaded
 * (the API only stores image paths; the files may not be deployed yet).
 */
export function ProductImage({
  src,
  alt,
  className,
}: {
  src?: string
  alt: string
  className?: string
}) {
  const [failedSrc, setFailedSrc] = useState<string>()

  if (src && failedSrc !== src) {
    return (
      <img
        src={src}
        alt={alt}
        loading="lazy"
        onError={() => setFailedSrc(src)}
        className={cn('object-cover', className)}
      />
    )
  }
  return (
    <div
      role="img"
      aria-label={alt}
      className={cn(
        'flex items-center justify-center bg-gradient-to-br from-secondary to-muted text-accent',
        className,
      )}
    >
      <Coffee className="size-10 opacity-70" aria-hidden="true" />
    </div>
  )
}
