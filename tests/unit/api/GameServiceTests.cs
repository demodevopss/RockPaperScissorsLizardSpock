using NUnit.Framework;
using RPSLS.Game.Api.Services;
using GameApi.Proto;

namespace RPSLS.Tests.Unit.Api
{
    [TestFixture]
    public class GameServiceTests
    {
        private IGameService _gameService;

        [SetUp]
        public void Setup()
        {
            _gameService = new GameService();
        }

        [TestCase(0, 0, Result.Tie)] // Rock vs Rock
        [TestCase(0, 1, Result.Challenger)] // Rock vs Paper
        [TestCase(0, 2, Result.Player)] // Rock vs Scissors
        [TestCase(0, 3, Result.Player)] // Rock vs Lizard
        [TestCase(0, 4, Result.Challenger)] // Rock vs Spock
        [TestCase(1, 0, Result.Player)] // Paper vs Rock
        [TestCase(1, 2, Result.Challenger)] // Paper vs Scissors
        [TestCase(2, 1, Result.Player)] // Scissors vs Paper
        [TestCase(4, 0, Result.Player)] // Spock vs Rock
        public void Check_ReturnsCorrectResult(int playerPick, int challengerPick, Result expectedResult)
        {
            // Act
            var result = _gameService.Check(playerPick, challengerPick);
            
            // Assert
            Assert.AreEqual(expectedResult, result);
        }

        [Test]
        public void Check_InvalidPlayerPick_ThrowsArgumentException()
        {
            // Arrange
            int invalidPick = 5;
            int validPick = 0;
            
            // Act & Assert
            Assert.Throws<ArgumentException>(() => _gameService.Check(invalidPick, validPick));
        }

        [Test]
        public void Check_InvalidChallengerPick_ThrowsArgumentException()
        {
            // Arrange
            int validPick = 0;
            int invalidPick = -1;
            
            // Act & Assert
            Assert.Throws<ArgumentException>(() => _gameService.Check(validPick, invalidPick));
        }

        [TestCase(-1)]
        [TestCase(5)]
        [TestCase(100)]
        public void Check_OutOfRangePicks_ThrowsArgumentException(int invalidPick)
        {
            // Act & Assert
            Assert.Throws<ArgumentException>(() => _gameService.Check(0, invalidPick));
            Assert.Throws<ArgumentException>(() => _gameService.Check(invalidPick, 0));
        }
    }
}
