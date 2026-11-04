package com.example.opsdesk;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import java.util.*;
@RestController
@RequestMapping("/api")
public class IncidentController {
 private final IncidentService service;
 public IncidentController(IncidentService service){this.service=service;}
 @GetMapping("/incidents") public List<Incident> all(){return service.all();}
 @GetMapping("/incidents/{id}") public Incident get(@PathVariable long id){return service.get(id);}
 @PostMapping("/incidents") @ResponseStatus(HttpStatus.CREATED)
 public Incident create(@Valid @RequestBody CreateIncidentRequest r){return service.create(r);}
 @PatchMapping("/incidents/{id}/status")
 public Incident status(@PathVariable long id,@Valid @RequestBody UpdateStatusRequest r){return service.status(id,r.status());}
 @GetMapping("/statistics") public Map<String,Long> stats(){return service.stats();}
}
