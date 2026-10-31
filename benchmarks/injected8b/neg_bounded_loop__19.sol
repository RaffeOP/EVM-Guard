pragma solidity 0.8.20;

contract Vault2904 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public deposits;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        reserve += msg.value;
    }
    address[] public members;

    function join() public {
        if (members.length < 8) members.push(msg.sender);
    }

    function creditAll() public {
        for (uint256 i = 0; i < 8; i++) {
            if (i < members.length) members[i].code.length;
        }
    }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }

    function totalDeposits() public view returns (uint256) { return reserve; }
}
