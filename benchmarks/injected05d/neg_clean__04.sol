pragma solidity 0.5.12;

contract Escrow8537 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public balances;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        supply += msg.value;
    }

    function totalDeposits() public view returns (uint256) { return supply; }
}
