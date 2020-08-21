(define (gimp-image-save-with-only-layer in-layer img in-filename)
  (let* (
    (the-width (car (gimp-image-width img)))
    (the-height (car (gimp-image-height img)))
    (the-type (car (gimp-image-base-type img)))
    (the-new-img (car (gimp-image-new the-width the-height the-type)))
    (the-copied-layer (car (gimp-layer-new-from-drawable in-layer the-new-img)))
    )
    (gimp-file-save RUN-NONINTERACTIVE the-new-img the-new-img in-filename in-filename)
  )
)

(define (gimp-extract-layers filename)

  (gimp-message (string-append "Loading " filename "..."))

  (let* (
         (img (car (gimp-file-load RUN-NONINTERACTIVE filename filename)))
         (layers (gimp-image-get-layers img))
         (num-layers (car layers))
         (layer-array (cadr layers))
         (export-file-name-prefix (string-append (substring filename 0 (- (string-length filename) 4)) "_layer"))
        )

    (gimp-message (string-append "Found " (number->string num-layers) " layers."))

    (let* ((i 0))
      (while (< i num-layers)
        (let* ((layer (aref layer-array i))
               (name (gimp-item-get-name layer))
               (export-file-name (string-append export-file-name-prefix (number->string i) ".jpg"))
               )
          (gimp-message (string-append "Layer number " (number->string i)))
          (gimp-image-save-with-only-layer layer img export-file-name)
        )
        (set! i (+ i 1))
      )
    )

    (gimp-image-clean-all img)
    (gimp-image-delete img)
  )
)
