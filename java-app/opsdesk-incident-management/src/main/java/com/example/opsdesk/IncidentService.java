package com.example.opsdesk;
import org.springframework.stereotype.Service;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
@Service
public class IncidentService {
 private final Map<Long,Incident> data = new ConcurrentHashMap<>();
 private final AtomicLong ids = new AtomicLong(1000);
 public IncidentService() {
  addSeed("API Gateway unavailable","Intermittent 502 responses from public API","API Gateway","Arun","CRITICAL","OPEN");
  addSeed("Database latency elevated","Checkout queries exceed latency threshold","Payments DB","Meera","HIGH","IN_PROGRESS");
  addSeed("TLS certificate expiring","Reporting certificate expires within 14 days","Reporting","Karthik","MEDIUM","OPEN");
  addSeed("Login page layout regression","Sign-in panel overlaps footer on small screens","Identity","Divya","HIGH","RESOLVED");
  addSeed("Nightly backup delayed","Scheduled backup completed late","Backup","Arun","LOW","RESOLVED");
 }
 private void addSeed(String t,String d,String s,String a,String p,String st) {
  long id=ids.incrementAndGet(); data.put(id,new Incident(id,t,d,s,a,p,st,Instant.now()));
 }
 public List<Incident> all() { return data.values().stream().sorted(Comparator.comparing(Incident::createdAt).reversed()).toList(); }
 public Incident get(long id) { Incident i=data.get(id); if(i==null) throw new NoSuchElementException("Incident "+id+" not found"); return i; }
 public Incident create(CreateIncidentRequest r) {
  String p=r.priority().toUpperCase(Locale.ROOT);
  if(!Set.of("LOW","MEDIUM","HIGH","CRITICAL").contains(p)) throw new IllegalArgumentException("Invalid priority");
  long id=ids.incrementAndGet();
  Incident i=new Incident(id,r.title().trim(),r.description().trim(),r.service().trim(),r.assignee().trim(),p,"OPEN",Instant.now());
  data.put(id,i); return i;
 }
 public Incident status(long id,String status) {
  String s=status.toUpperCase(Locale.ROOT);
  if(!Set.of("OPEN","IN_PROGRESS","RESOLVED").contains(s)) throw new IllegalArgumentException("Invalid status");
  Incident old=get(id);
  Incident updated=new Incident(old.id(),old.title(),old.description(),old.service(),old.assignee(),old.priority(),s,old.createdAt());
  data.put(id,updated); return updated;
 }
 public Map<String,Long> stats() {
  long open=data.values().stream().filter(i->i.status().equals("OPEN")).count();
  long progress=data.values().stream().filter(i->i.status().equals("IN_PROGRESS")).count();
  long resolved=data.values().stream().filter(i->i.status().equals("RESOLVED")).count();
  return Map.of("total",(long)data.size(),"open",open,"inProgress",progress,"resolved",resolved);
 }
}
