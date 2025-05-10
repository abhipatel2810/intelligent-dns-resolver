from locust import HttpUser, task, between

class DnsTestUser(HttpUser):
    wait_time = between(1, 4)  # Simulate realistic pacing

    @task(4)
    def query_MX(self):
        self.client.get("/resolve?domain=example.com&type=MX")

    @task(3)
    def resolve_a_record(self):
        self.client.get("/resolve?domain=example.com&type=A")

    @task(2)
    def resolve_cname_record(self):
        self.client.get("/resolve?domain=example.com&type=CNAME")

    @task(1)
    def resolve_aaaa_record(self):
        self.client.get("/resolve?domain=example.com&type=AAAA")
