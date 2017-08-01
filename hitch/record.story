Serve YAML:
  preconditions:
    example.yaml: |
      request:
        path: /hello
        method: GET
      response:
        code: 200
        content: how do you do?
    code: |
      import hitchhttp
      
      servers = hitchhttp.Servers(
          example=hitchhttp.ServeYAML(
            "http://localhost:10000",
            "example.yaml",
          ),
      )
        
      servers.serve()
  scenario:
    - Server starts
    - Request:
        request:
          path: hello
          method: GET
        response:
          code: 200
          content: how do you do?
    - Server ends normally
