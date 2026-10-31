pragma solidity 0.8.20;

contract Vault1224 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public balances;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        supply += msg.value;
    }

    function totalDeposits() public view returns (uint256) { return supply; }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
