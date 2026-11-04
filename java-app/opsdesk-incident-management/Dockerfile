FROM eclipse-temurin:17-jre
WORKDIR /apps
COPY /home/ubuntu/workspace/jen-app/java-app/opsdesk-incident-management/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java","-jar","/apps/app.jar"]
