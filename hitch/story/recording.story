Recording:
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
          recording=hitchhttp.InterceptServer(
            10001,
            pointed_at="http://localhost:10000",
          ),
      )
        
      servers.serve(
        "Servers started",
        database_filename="recordings.sqlite",
      )
    analysis_code: |
      import hitchhttp
      
      hitchhttp.Recording("recordings.sqlite")\
               .from_server("recording")\
               .write_yaml("recording.yaml")
  scenario:
    - Server starts:
        message: Servers started
    - Request:
        request:
          url: http://localhost:10001/hello
          method: GET
        expected_response:
          code: 200
          content: how do you do?
    - Server stopped normally
    - Run analysis code
    - File contains:
        filename: recording.yaml
        contents: |
          - request:
              path: /hello
              method: get
            response:
              code: 200
              content: how do you do?
