import { IsDateString, IsOptional, IsString, MaxLength, MinLength } from 'class-validator';

export class MarketQueryDto {
  @IsOptional()
  @IsString()
  @MaxLength(2000)
  coin_ids?: string;

  @IsOptional()
  @IsString()
  @MinLength(2)
  @MaxLength(10)
  currency?: string;

  @IsOptional()
  @IsDateString()
  start_date?: string;

  @IsOptional()
  @IsDateString()
  end_date?: string;
}
