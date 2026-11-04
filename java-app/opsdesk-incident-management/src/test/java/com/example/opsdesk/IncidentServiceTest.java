package com.example.opsdesk;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import java.util.NoSuchElementException;
import static org.junit.jupiter.api.Assertions.*;
class IncidentServiceTest {
 private IncidentService service;
 @BeforeEach void setup(){service=new IncidentService();}
 @Test void seedsFiveIncidents(){assertEquals(5,service.all().size());}
 @Test void createsIncidentAsOpen(){var x=service.create(new CreateIncidentRequest("Cache down","Cache nodes not responding","Cache","Nisha","CRITICAL"));assertEquals("OPEN",x.status());assertEquals("Cache down",x.title());}
 @Test void updatesStatus(){var x=service.status(1001,"RESOLVED");assertEquals("RESOLVED",x.status());}
 @Test void statisticsAddUp(){var s=service.stats();assertEquals(s.get("total"),s.get("open")+s.get("inProgress")+s.get("resolved"));}
 @Test void unknownIdThrows(){assertThrows(NoSuchElementException.class,()->service.get(999999));}
 @Test void rejectsInvalidStatus(){assertThrows(IllegalArgumentException.class,()->service.status(1001,"BROKEN"));}
}
