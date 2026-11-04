package com.example.opsdesk;
import jakarta.validation.constraints.NotBlank;
public record UpdateStatusRequest(@NotBlank String status) {}
