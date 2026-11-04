package com.example.opsdesk;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
public record CreateIncidentRequest(@NotBlank @Size(max=100) String title,
 @NotBlank @Size(max=1000) String description, @NotBlank @Size(max=80) String service,
 @NotBlank @Size(max=80) String assignee, @NotNull String priority) {}
