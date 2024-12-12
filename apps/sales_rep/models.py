from django.db import models

class SalesAgent(models.Model):
    agent_id = models.CharField(
        max_length=50, unique=True, help_text="Sales Agent Identifier"
    )
    agent_name = models.CharField(
        max_length=255, help_text="Sales Agent Name"
    )
    telephone = models.CharField(
        max_length=20, blank=True, null=True, help_text="Telephone"
    )
    email = models.EmailField(
        blank=True, null=True, help_text="Email"
    )
    branch = models.ForeignKey(
        'branches.Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_agents',
        help_text="Branch the Sales Agent belongs to"
    )

    def __str__(self):
        return f"{self.agent_id} - {self.agent_name}"

    def save(self, *args, **kwargs):
        if not self.agent_id:
            last_agent = SalesAgent.objects.order_by('id').last()
            if last_agent and last_agent.agent_id.startswith("AGT"):
                last_number = int(last_agent.agent_id[3:])  # Extract the number part
                self.agent_id = f"AGT{last_number + 1:04d}"  # Increment and pad with zeros
            else:
                self.agent_id = "AGT0001"  # Start from AGT0001
        super().save(*args, **kwargs)