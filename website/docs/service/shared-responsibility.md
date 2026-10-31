---
title: Shared responsibility
sidebar_position: 8
description: What Patternode is responsible for, and what you are.
---

# Shared responsibility

| Area | Patternode | You |
|---|---|---|
| The service | Available, fast, correct and secure to the service levels of your plan | Choosing the plan your use needs |
| Your keys | Never seeing a live key after it is created; revoking within a minute of your request | Keeping keys in a secret store; rotating them; scoping them narrowly |
| Network | The edge and everything behind it | Your network to the edge; private connectivity on your side |
| Your data | Keeping it in your jurisdiction; keeping nothing of a finished series; encrypting what it holds | Sending only what is needed; naming series opaquely; keeping the mapping |
| Segments | Returning them deterministically per profile version | Storing them; drawing them; deciding what they mean for your users |
| Real-time | Applying appends in sequence, exactly once; delivering events at least once | Assigning sequences; retrying with the same sequence or key; deduplicating events |
| Failover | Moving your traffic, losing nothing acknowledged | A client that retries, reconnects and resumes ([Resilience](resilience.md)) |
| Capacity | Provisioning your plan's figures; adding more within 10 business days of notice | Telling Patternode before you go beyond them |
| Change | Releasing safely, outside your blackout periods | Setting blackout periods; reading the changelog; pinning profile versions where you need to |
| Incidents | Detecting, communicating and reporting as [Support](support.md) says | Watching the status page; opening Severity 1 by phone |
| Compliance | The assurance in [Compliance](compliance.md) | Your own regulatory obligations |
