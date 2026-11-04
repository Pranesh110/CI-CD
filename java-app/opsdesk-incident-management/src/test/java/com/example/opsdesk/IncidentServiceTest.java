package com.example.opsdesk;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.NoSuchElementException;

import static org.junit.jupiter.api.Assertions.*;

class IncidentServiceTest {

    private IncidentService service;

    @BeforeEach
    void setup() {
        service = new IncidentService();
    }

    @Test
    void seedsFiveIncidents() {
        assertEquals(5, service.all().size());
    }

    @Test
    void createsIncidentAsOpen() {

        var incident = service.create(
                new CreateIncidentRequest(
                        "Cache down",
                        "Cache nodes not responding",
                        "Cache",
                        "Nisha",
                        "HIGH"
                )
        );

        assertEquals("OPEN", incident.status());
        assertEquals(6, service.all().size());
    }

    @Test
    void updatesStatus() {

        var incident = service.status(1001, "RESOLVED");

        assertEquals("RESOLVED", incident.status());
    }

    @Test
    void statisticsAddUp() {

        var stats = service.stats();

        assertEquals(
                stats.get("total"),
                stats.get("open")
                        + stats.get("inProgress")
                        + stats.get("resolved")
        );
    }

    @Test
    void unknownIdThrows() {

        assertThrows(
                NoSuchElementException.class,
                () -> service.get(999999)
        );
    }

    @Test
    void rejectsInvalidStatus() {

        assertThrows(
                IllegalArgumentException.class,
                () -> service.status(1001, "BROKEN")
        );
    }
}
