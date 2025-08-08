FROM mcr.microsoft.com/dotnet/sdk:5.0-focal AS build
WORKDIR /src

# Only protoc is required; Grpc.Tools NuGet provides compiler plugins during msbuild
RUN apt-get update \
    && apt-get install -y --no-install-recommends protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

# Restore and publish
COPY Source/ ./Source/
COPY Source/RPSLS.sln ./Source/
RUN dotnet restore ./Source/RPSLS.sln

RUN dotnet publish ./Source/Services/RPSLS.Game.Api/RPSLS.Game.Api.csproj \
    -c Release -o /app/publish --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:5.0-focal AS runtime
WORKDIR /app
ENV ASPNETCORE_URLS=http://+:8080
EXPOSE 8080
COPY --from=build /app/publish ./
ENTRYPOINT ["dotnet", "RPSLS.Game.Api.dll"]
