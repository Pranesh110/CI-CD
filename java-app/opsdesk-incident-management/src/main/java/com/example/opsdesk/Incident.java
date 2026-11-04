package com.example.opsdesk;
import java.time.Instant;
public record Incident(long id, String title, String description, String service, String assignee,
                       String priority, String status, Instant createdAt) {}
