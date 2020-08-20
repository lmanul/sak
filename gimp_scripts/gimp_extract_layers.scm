(define (gimp-extract-layers filename)

  (display (string-append "Loading " filename "...")) (newline)

  (let ((myimg (car (gimp-file-load RUN-NONINTERACTIVE filename filename)))))

  (let ((layer-count (car (gimp-image-get-layers myimg)))))

  (display (string-append "Found " layer-count " layers.")) (newline)

  (gimp-image-delete myimg)
)
