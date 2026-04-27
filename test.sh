curl -X POST "https://10.110.0.105:8443/api/auth" \
-H  "Accept: application/vnd.ceph.api.v1.0+json" \
-H  "Content-Type: application/json" \
-d '{"username": "admin", "password": "fnslt10!"}' --insecure


curl -X GET "https://10.110.0.105:8443/api/health/full" \
-H  "Accept: application/vnd.ceph.api.v1.0+json" \
-H  "Authorization: Bearer "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJjZXBoLWRhc2hib2FyZCIsImp0aSI6ImZlNzdhNzY0LWNlZWYtNGVkZS1hOWY5LTMwZjU2MmFkNWFiMSIsImV4cCI6MTc3NzMwODI5MywiaWF0IjoxNzc3Mjc5NDkzLCJ1c2VybmFtZSI6ImFkbWluIn0.Lb6bUhngrVxYkPcSRYQSAp_hKJct6KUN970FmuoAE-E"" \
--insecure