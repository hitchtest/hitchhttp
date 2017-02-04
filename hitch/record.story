Record HTTP request:
  scenario:
    - Run command: import hitchhttp
    - Run command: |
        def response(request):
          return hitchhttp.record(request)
