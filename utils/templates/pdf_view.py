from easy_pdf.views import PDFTemplateView


class PDFView(PDFTemplateView):
    template_name = 'mandates.template.html'
    base_url = 'file://' + settings.STATIC_ROOT
    download_filename = 'mandates.pdf'
