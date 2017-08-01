Serve YAML:
  preconditions:
    example.yaml: |
      - request:
          path: /hello
          method: get
        response:
          code: 200
          content: how do you do?
    code: |
      import hitchhttp
      
      servers = hitchhttp.ServerGroup(
          example=hitchhttp.ServeYAML(
            10000,
            "example.yaml",
          ),
      )
        
      servers.serve("Servers started")
  scenario:
    - Server starts:
        message: Servers started
    - Request:
        request:
          url: http://localhost:10000/hello
          method: GET
        expected_response:
          code: 200
          content: how do you do?
    - Server stopped normally
