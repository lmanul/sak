(define (gimp-extract-layers filename)

  (display (string-append "Loading " filename "...")) (newline) (newline)

  (let* (
         (myimg (car (gimp-file-load RUN-NONINTERACTIVE filename filename)))
         (layer-count (car (gimp-image-get-layers myimg)))
        )


    (gimp-message (string-append "Found " (number->string layer-count) " layers.")) (newline)
    (gimp-image-delete myimg)
  )
)
