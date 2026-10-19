import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcryptjs';
import { AuthService } from './auth.service';

describe('AuthService', () => {
  it('does not include the stored password hash in the login response', async () => {
    const user = {
      id: '3fa85f64-5717-4562-b3fc-2c963f66afa6',
      email: 'user@example.com',
      password: bcrypt.hashSync('CorrectPassword123', 4),
    };
    const userRepository = {
      findOne: jest.fn().mockResolvedValue(user),
    };
    const jwtService = {
      sign: jest.fn().mockReturnValue('jwt-token'),
    } as unknown as JwtService;
    const service = new AuthService(userRepository as never, jwtService);
    const response = await service.login({
      email: user.email,
      password: 'CorrectPassword123',
    });

    expect(response).not.toHaveProperty('password');
    expect(JSON.stringify(response)).not.toContain(user.password);
    expect(response).toHaveProperty('token', 'jwt-token');
  });
});
