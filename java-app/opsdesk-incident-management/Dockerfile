FROM eclipse-temurin:17-jre
WORKDIR /apps
COPY /var/lib/jenkins/workspace/java-cicd/java-app/opsdesk-incident-management/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java","-jar","/apps/app.jar"]
