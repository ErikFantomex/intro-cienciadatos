import { IsArray, IsDateString, IsIn, IsString, MaxLength, MinLength } from 'class-validator';

export class IngestCryptoDto {
  @IsArray()
  @IsString({ each: true })
  @MinLength(1, { each: true })
  @MaxLength(100, { each: true })
  coin_ids: string[];

  @IsString()
  @MinLength(2)
  @MaxLength(10)
  currency: string;

  @IsDateString()
  start_date: string;

  @IsDateString()
  end_date: string;
}
