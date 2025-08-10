using NUnit.Framework;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Http;
using Moq;
using RPSLS.Game.Api.Services;
using System.Collections.Generic;
using System.Linq;
using System;

namespace RPSLS.Tests.Unit.Api
{
    [TestFixture]
    public class ChallengerServiceTests
    {
        private Mock<IConfiguration> _mockConfiguration;
        private Mock<ILogger<ChallengerService>> _mockLogger;
        private Mock<IHttpClientFactory> _mockHttpClientFactory;
        private ChallengerService _challengerService;

        [SetUp]
        public void Setup()
        {
            _mockConfiguration = new Mock<IConfiguration>();
            _mockLogger = new Mock<ILogger<ChallengerService>>();
            _mockHttpClientFactory = new Mock<IHttpClientFactory>();

            // Mock configuration
            var challengersSection = new Mock<IConfigurationSection>();
            challengersSection.Setup(x => x.GetChildren()).Returns(GetMockChallengers());
            _mockConfiguration.Setup(x => x.GetSection("Challengers")).Returns(challengersSection.Object);

            _challengerService = new ChallengerService(_mockConfiguration.Object, _mockLogger.Object, _mockHttpClientFactory.Object);
        }

        [Test]
        public void Challengers_ReturnsConfiguredChallengers()
        {
            // Act
            var challengers = _challengerService.Challengers;
            
            // Assert
            Assert.IsNotNull(challengers);
            Assert.AreEqual(2, challengers.Count());
            Assert.IsTrue(challengers.Any(c => c.Info.Name == "dotnet"));
            Assert.IsTrue(challengers.Any(c => c.Info.Name == "python"));
        }

        [Test]
        public void SelectChallenger_ValidRequest_ReturnsChallenger()
        {
            // Arrange
            var request = new GameApi.Proto.GameRequest
            {
                Challenger = "dotnet",
                Username = "testuser",
                Pick = 0
            };

            // Act
            var challenger = _challengerService.SelectChallenger(request);
            
            // Assert
            Assert.IsNotNull(challenger);
            Assert.AreEqual("dotnet", challenger.Info.Name);
        }

        [Test]
        public void SelectChallenger_InvalidChallenger_ThrowsException()
        {
            // Arrange
            var request = new GameApi.Proto.GameRequest
            {
                Challenger = "nonexistent",
                Username = "testuser",
                Pick = 0
            };

            // Act & Assert
            Assert.Throws<InvalidOperationException>(() => _challengerService.SelectChallenger(request));
        }

        private IEnumerable<IConfigurationSection> GetMockChallengers()
        {
            var dotnetChallenger = new Mock<IConfigurationSection>();
            dotnetChallenger.Setup(x => x["Name"]).Returns("dotnet");
            dotnetChallenger.Setup(x => x["DisplayName"]).Returns(".NET");
            dotnetChallenger.Setup(x => x["Url"]).Returns("https://jsonplaceholder.typicode.com");

            var pythonChallenger = new Mock<IConfigurationSection>();
            pythonChallenger.Setup(x => x["Name"]).Returns("python");
            pythonChallenger.Setup(x => x["DisplayName"]).Returns("Python");
            pythonChallenger.Setup(x => x["Url"]).Returns("https://jsonplaceholder.typicode.com");

            return new[] { dotnetChallenger.Object, pythonChallenger.Object };
        }
    }
}
