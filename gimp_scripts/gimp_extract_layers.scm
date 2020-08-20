(define (gimp-extract-layers filename)

(display (string-append "Loading " filename "...")) (newline)

(let ((myimg (gimp-file-load RUN-NONINTERACTIVE filename filename))))

(gimp-quit FALSE)
)
