const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const path = require('path');

// Load protobuf definition
const PROTO_PATH = path.join(__dirname, '../../../Source/Services/RPSLS.Game.Api/Protos/GameApi.proto');
const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
    keepCase: true,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true
});

const gameProto = grpc.loadPackageDefinition(packageDefinition).GameManagementApi;

// Test configuration
const GRPC_SERVER = process.env.GRPC_SERVER || '192.168.64.153:30082';
const client = new gameProto.BotGameManager(GRPC_SERVER, grpc.credentials.createInsecure());

// Test cases
describe('BotGameManager gRPC Service', () => {
    test('GetChallengers - should return list of challengers', (done) => {
        client.GetChallengers({}, (error, response) => {
            expect(error).toBeNull();
            expect(response).toBeDefined();
            expect(response.count).toBeGreaterThan(0);
            expect(response.challengers).toBeDefined();
            expect(Array.isArray(response.challengers)).toBe(true);
            
            // Verify challenger structure
            if (response.challengers.length > 0) {
                const challenger = response.challengers[0];
                expect(challenger.name).toBeDefined();
                expect(challenger.displayName).toBeDefined();
            }
            
            done();
        });
    });

    test('DoPlay - should handle valid game request', (done) => {
        const gameRequest = {
            challenger: 'dotnet',
            username: 'testuser',
            twitterLogged: false,
            pick: 0 // Rock
        };

        client.DoPlay(gameRequest, (error, response) => {
            expect(error).toBeNull();
            expect(response).toBeDefined();
            expect(response.challenger).toBe('dotnet');
            expect(response.user).toBe('testuser');
            expect(response.userPick).toBe(0);
            expect(response.challengerPick).toBeGreaterThanOrEqual(0);
            expect(response.challengerPick).toBeLessThanOrEqual(4);
            expect(response.isValid).toBe(true);
            expect(['Tie', 'Player', 'Challenger']).toContain(response.result);
            
            done();
        });
    });

    test('DoPlay - should handle all pick combinations', (done) => {
        const picks = [0, 1, 2, 3, 4]; // Rock, Paper, Scissors, Lizard, Spock
        let completedTests = 0;
        
        picks.forEach(pick => {
            const gameRequest = {
                challenger: 'python',
                username: 'testuser',
                twitterLogged: false,
                pick: pick
            };

            client.DoPlay(gameRequest, (error, response) => {
                expect(error).toBeNull();
                expect(response).toBeDefined();
                expect(response.userPick).toBe(pick);
                expect(response.isValid).toBe(true);
                
                completedTests++;
                if (completedTests === picks.length) {
                    done();
                }
            });
        });
    });

    test('DoPlay - should handle invalid challenger', (done) => {
        const gameRequest = {
            challenger: 'nonexistent',
            username: 'testuser',
            twitterLogged: false,
            pick: 0
        };

        client.DoPlay(gameRequest, (error, response) => {
            expect(error).toBeDefined();
            expect(error.code).toBe(grpc.status.INVALID_ARGUMENT);
            done();
        });
    });

    afterAll(() => {
        client.close();
    });
});

// Performance tests
describe('BotGameManager Performance', () => {
    test('GetChallengers - response time under 1000ms', (done) => {
        const startTime = Date.now();
        
        client.GetChallengers({}, (error, response) => {
            const responseTime = Date.now() - startTime;
            expect(responseTime).toBeLessThan(1000);
            expect(error).toBeNull();
            done();
        });
    });

    test('DoPlay - response time under 2000ms', (done) => {
        const startTime = Date.now();
        const gameRequest = {
            challenger: 'java',
            username: 'perftest',
            twitterLogged: false,
            pick: 2
        };

        client.DoPlay(gameRequest, (error, response) => {
            const responseTime = Date.now() - startTime;
            expect(responseTime).toBeLessThan(2000);
            expect(error).toBeNull();
            done();
        });
    });
});
