(define (boolean->string val) (if val "#t" "#f"))

(define (show-only-layer in-layer img)
  (gimp-message (string-append "Hiding all layers but " (number->string in-layer)))
  (let* (
         (layers (gimp-image-get-layers img))
         (num-layers (car layers))
         (layer-array (cadr layers))
        ;; )
    )
    (let* (
           (i 0)
           )
      (while (< i num-layers)
        (let* (
          (layer (aref layer-array i)))
          (if (= layer in-layer)
              (gimp-item-set-visible layer TRUE)
              (gimp-item-set-visible layer FALSE))
        )
        (set! i (+ i 1))
      )
    )
  )
)

(define (gimp-extract-layers filename)

  (gimp-message (string-append "Loading " filename "..."))

  (let* (
         (img (car (gimp-file-load RUN-NONINTERACTIVE filename filename)))
         (layers (gimp-image-get-layers img))
         (num-layers (car layers))
         (layer-array (cadr layers))
        )

    (gimp-message (string-append "Found " (number->string num-layers) " layers."))

    (let* ((i 0))
      (while (< i num-layers)
        (let* ((layer (aref layer-array i))
               (name (gimp-item-get-name layer))
               )
          (gimp-message (string-append "Layer number " (number->string i)))
          ;; (gimp-message (boolean->string (car (gimp-layer-is-floating-sel layer))))
          (show-only-layer layer img)
        )
        (set! i (+ i 1))
      )
    )

    (gimp-image-clean-all img)
    (gimp-image-delete img)
  )
)
