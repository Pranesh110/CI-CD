FROM eclipse-temurin:17-jre

WORKDIR /apps

COPY target/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]