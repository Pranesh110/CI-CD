package com.example.opsdesk;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.bind.MethodArgumentNotValidException;
import java.util.Map;
@RestControllerAdvice
public class ApiErrors {
 @ExceptionHandler(NoSuchElementException.class) @ResponseStatus(HttpStatus.NOT_FOUND)
 public Map<String,String> missing(Exception e){return Map.of("error",e.getMessage());}
 @ExceptionHandler({IllegalArgumentException.class,MethodArgumentNotValidException.class})
 @ResponseStatus(HttpStatus.BAD_REQUEST)
 public Map<String,String> invalid(Exception e){return Map.of("error","Invalid request: "+e.getMessage());}
}
