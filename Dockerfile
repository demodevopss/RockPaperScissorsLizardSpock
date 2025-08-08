## Multi-stage Dockerfile for RPSLS.Game.Api (.NET 5)

# Build stage
FROM mcr.microsoft.com/dotnet/sdk:5.0 AS build
WORKDIR /src

# Copy solution and restore
COPY Source/ ./Source/
COPY Source/RPSLS.sln ./Source/
RUN dotnet restore ./Source/RPSLS.sln

# Publish specific service
RUN dotnet publish ./Source/Services/RPSLS.Game.Api/RPSLS.Game.Api.csproj \
    -c Release -o /app/publish --no-restore

# Runtime stage
FROM mcr.microsoft.com/dotnet/aspnet:5.0 AS runtime
WORKDIR /app
ENV ASPNETCORE_URLS=http://+:8080
EXPOSE 8080
COPY --from=build /app/publish ./
ENTRYPOINT ["dotnet", "RPSLS.Game.Api.dll"]


