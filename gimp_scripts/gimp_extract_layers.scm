(define (gimp-extract-layers filename)

  (gimp-message (string-append "Loading " filename "..."))

  (let* (
         (myimg (car (gimp-file-load RUN-NONINTERACTIVE filename filename)))
         (layer-count (car (gimp-image-get-layers myimg)))
         (layer-ids (cadr (gimp-image-get-layers myimg)))
        )

    (gimp-message (string-append "Found " (number->string layer-count) " layers."))

    (let* ((current-layer-index 0))
      (while (< current-layer-index layer-count)
        (gimp-message (string-append "Layer " (number->string current-layer-index)))
        (let* ((current-layer (vector-ref layer-ids current-layer-index))
               (current-layer-name (gimp-item-get-name current-layer))
               )
          ;; (gimp-message (string-append "Hop " (number->string current-layer)))
          ;; (gimp-message (string-append "Hip " (class-of current-layer-name)))
          ;; (gimp-message (string-append "Hip " (number->string current-layer-name)))
          ;; (gimp-message (string-append "Layer " current-layer-name))
        )
        (set! current-layer-index (+ current-layer-index 1))
      )
    )

    (gimp-image-clean-all myimg)
    (gimp-image-delete myimg)
  )
)
