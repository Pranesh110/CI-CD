package com.example.opsdesk;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
@SpringBootTest @AutoConfigureMockMvc
class IncidentControllerIntegrationTest {
 @Autowired MockMvc mvc; @Autowired ObjectMapper mapper;
 @Test void listIncidents() throws Exception {mvc.perform(get("/api/incidents")).andExpect(status().isOk()).andExpect(jsonPath("$.length()").value(5));}
 @Test void createIncident() throws Exception {
  var body=new CreateIncidentRequest("Queue backlog","Messages delayed","Messaging","Ravi","HIGH");
  mvc.perform(post("/api/incidents").contentType(MediaType.APPLICATION_JSON).content(mapper.writeValueAsString(body))).andExpect(status().isCreated()).andExpect(jsonPath("$.status").value("OPEN"));
 }
 @Test void rejectsBlankTitle() throws Exception {
  mvc.perform(post("/api/incidents").contentType(MediaType.APPLICATION_JSON).content("{\"title\":\"\",\"description\":\"desc\",\"service\":\"svc\",\"assignee\":\"Sam\",\"priority\":\"HIGH\"}")).andExpect(status().isBadRequest());
 }
 @Test void updateStatus() throws Exception {
  mvc.perform(patch("/api/incidents/1001/status").contentType(MediaType.APPLICATION_JSON).content("{\"status\":\"RESOLVED\"}")).andExpect(status().isOk()).andExpect(jsonPath("$.status").value("RESOLVED"));
 }
 @Test void actuatorHealthIsUp() throws Exception {mvc.perform(get("/actuator/health")).andExpect(status().isOk()).andExpect(jsonPath("$.status").value("UP"));}
}
